package views.hangar
{
    import flash.display.Shape;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.events.MouseEvent;
    import flash.filters.DropShadowFilter;
    import flash.geom.Point;
    import flash.text.AntiAliasType;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFormat;

    import net.wg.data.Aliases;
    import net.wg.data.constants.generated.LAYER_NAMES;
    import net.wg.gui.components.containers.MainViewContainer;
    import net.wg.infrastructure.base.AbstractView;
    import net.wg.infrastructure.events.LoaderEvent;
    import net.wg.infrastructure.interfaces.ISimpleManagedContainer;
    import net.wg.infrastructure.interfaces.IView;
    import net.wg.infrastructure.managers.impl.ContainerManagerBase;

    public class MarksOnGunHangar extends AbstractView
    {
        private static const CHIP_GAP:Number = 8.0;
        private static const CHIP_HEIGHT:Number = 34.0;

        private var _container:Sprite;
        private var _card:Sprite;
        private var _accent:Shape;
        private var _chipLayer:Shape;
        private var _lineLayer:Shape;
        private var _stars:Vector.<Sprite>;
        private var _headerField:TextField;
        private var _vehicleField:TextField;
        private var _percentField:TextField;
        private var _nextField:TextField;
        private var _statsField:TextField;
        private var _targetsField:TextField;
        private var _masteryField:TextField;
        private var _wn8Field:TextField;
        private var _winrateField:TextField;
        private var _battlesField:TextField;
        private var _dragging:Boolean = false;
        private var _cfg:Object = null;
        private var _data:Object = null;
        private var _attached:Boolean = false;

        public var py_log:Function;
        public var py_savePosition:Function;

        public function MarksOnGunHangar()
        {
            super();
        }

        override protected function configUI() : void
        {
            super.configUI();
            initializeUI();
            addManagerListeners();
            addEventListener(Event.ADDED_TO_STAGE, onAddedToStage, false, 0, true);
            // Apply any config/data that may have arrived before the view finished initializing.
            if (_cfg != null)
            {
                redraw();
                updateVisibility();
            }
            if (_data != null)
            {
                render();
            }
        }

        override protected function onDispose() : void
        {
            removeDragListeners();
            removeManagerListeners();
            removeStageListeners();
            removeEventListener(Event.ADDED_TO_STAGE, onAddedToStage);
            super.onDispose();
        }

        public function as_applyConfig(data:Object) : void
        {
            _cfg = data;
            if (_container != null)
            {
                redraw();
                updateVisibility();
            }
        }

        public function as_updateData(data:Object) : void
        {
            _data = data;
            if (_container != null)
            {
                render();
            }
        }

        public function as_setVisible(value:Boolean) : void
        {
            if (_container)
            {
                _container.visible = value;
            }
        }

        private function initializeUI() : void
        {
            _container = new Sprite();
            _container.mouseChildren = true;
            _container.filters = [new DropShadowFilter(0, 0, 0x000000, 0.38, 18, 18, 1.5, 2)];

            _card = new Sprite();
            _accent = new Shape();
            _chipLayer = new Shape();
            _lineLayer = new Shape();
            _container.addChild(_card);
            _container.addChild(_accent);
            _container.addChild(_lineLayer);
            _container.addChild(_chipLayer);

            _headerField = createTextField(12, 24, true);
            _vehicleField = createTextField(20, 28, true);
            _percentField = createTextField(34, 40, true);
            _nextField = createTextField(12, 18, false);
            _statsField = createTextField(12, 22, false);
            _targetsField = createTextField(11, 18, false);
            _masteryField = createTextField(11, CHIP_HEIGHT, false);
            _wn8Field = createTextField(11, CHIP_HEIGHT, false);
            _winrateField = createTextField(11, CHIP_HEIGHT, false);
            _battlesField = createTextField(11, 16, false);

            _container.addChild(_headerField);
            _container.addChild(_vehicleField);
            _container.addChild(_percentField);
            _container.addChild(_nextField);
            _container.addChild(_statsField);
            _container.addChild(_targetsField);
            _container.addChild(_masteryField);
            _container.addChild(_wn8Field);
            _container.addChild(_winrateField);
            _container.addChild(_battlesField);

            _stars = new Vector.<Sprite>();
            for (var i:int = 0; i < 3; i++)
            {
                var star:Sprite = new Sprite();
                _stars.push(star);
                _container.addChild(star);
            }

            addChild(_container);
            locateExistingHangar();
        }

        private function addManagerListeners() : void
        {
            if (App.containerMgr)
            {
                ContainerManagerBase(App.containerMgr).loader.addEventListener(LoaderEvent.VIEW_LOADED, onViewLoaded, false, 0, true);
            }
        }

        private function removeManagerListeners() : void
        {
            if (App.containerMgr)
            {
                ContainerManagerBase(App.containerMgr).loader.removeEventListener(LoaderEvent.VIEW_LOADED, onViewLoaded);
            }
        }

        private function createTextField(size:Number, height:Number, bold:Boolean) : TextField
        {
            var field:TextField = new TextField();
            field.autoSize = TextFieldAutoSize.NONE;
            field.multiline = true;
            field.wordWrap = true;
            field.selectable = false;
            field.mouseEnabled = false;
            field.mouseWheelEnabled = false;
            field.antiAliasType = AntiAliasType.ADVANCED;
            field.defaultTextFormat = new TextFormat("$FieldFont", size, 0xFFFFFF, bold);
            field.height = height;
            field.filters = [new DropShadowFilter(0, 0, 0x000000, 0.7, 4, 4, 2, 2)];
            return field;
        }

        private function locateExistingHangar() : void
        {
            var viewContainer:MainViewContainer = getContainer(LAYER_NAMES.VIEWS) as MainViewContainer;
            if (viewContainer == null)
            {
                return;
            }
            for (var idx:int = 0; idx < viewContainer.numChildren; idx++)
            {
                processView(viewContainer.getChildAt(idx) as IView);
            }
        }

        private function onViewLoaded(event:LoaderEvent) : void
        {
            processView(event.view as IView);
        }

        private function onAddedToStage(event:Event) : void
        {
            addStageListeners();
            positionContainer();
        }

        private function processView(view:IView) : void
        {
            if (view == null || view.as_config == null || view.as_config.alias != Aliases.LOBBY_HANGAR)
            {
                return;
            }
            if (_container.parent != view)
            {
                view.addChild(_container);
            }
            if (!_attached)
            {
                _attached = true;
            }
            redraw();
            render();
            updateVisibility();
        }

        private function addStageListeners() : void
        {
            if (stage != null)
            {
                stage.addEventListener(Event.RESIZE, onStageResize, false, 0, true);
            }
        }

        private function removeStageListeners() : void
        {
            if (stage != null)
            {
                stage.removeEventListener(Event.RESIZE, onStageResize);
            }
        }

        private function onStageResize(event:Event) : void
        {
            positionContainer();
        }

        private function redraw() : void
        {
            if (_cfg == null || _container == null)
            {
                return;
            }

            var width:Number = Number(_cfg.width || 360);
            var height:Number = Number(_cfg.height || 188);
            var bgColor:uint = uint(_cfg.backgroundColor || 0x101114);
            var bgAlpha:Number = Number(_cfg.backgroundAlpha || 0.94);
            var outline:uint = uint(_cfg.outlineColor || 0x2B2D33);
            var line:uint = parseColor(String(_cfg.lineColor || "#262A31"));
            var accent:uint = parseColor(String(_cfg.accentColor || "#E2C07A"));
            var accentSoft:uint = parseColor(String(_cfg.accentSoftColor || "#3A2B17"));

            _card.graphics.clear();
            _card.graphics.lineStyle(1, outline, 1);
            _card.graphics.beginFill(bgColor, bgAlpha);
            drawRoundRect(_card.graphics, 0, 0, width, height, 18);
            _card.graphics.endFill();
            _card.graphics.lineStyle(1, 0xFFFFFF, 0.03);
            drawRoundRect(_card.graphics, 1, 1, width - 2, height - 2, 16);

            _accent.graphics.clear();
            _accent.graphics.beginFill(accentSoft, 0.26);
            drawRoundRect(_accent.graphics, 0, 0, width, 32, 18);
            _accent.graphics.endFill();
            _accent.graphics.beginFill(accent, 1);
            drawRoundRect(_accent.graphics, 18, 13, 52, 3, 3);
            _accent.graphics.endFill();

            _lineLayer.graphics.clear();
            _lineLayer.graphics.lineStyle(1, line, 1);
            _lineLayer.graphics.moveTo(18, 126);
            _lineLayer.graphics.lineTo(width - 18, 126);
            _lineLayer.graphics.moveTo(18, height - 24);
            _lineLayer.graphics.lineTo(width - 18, height - 24);

            _chipLayer.graphics.clear();
            layoutFields(width, height);
            positionContainer();
            updateDragMode();
        }

        private function layoutFields(width:Number, height:Number) : void
        {
            _headerField.width = width - 32;
            _vehicleField.width = width - 140;
            _percentField.width = width - 160;
            _nextField.width = width - 160;
            _statsField.width = width - 32;
            _targetsField.width = width - 32;
            _battlesField.width = width - 32;

            _headerField.x = 18;
            _headerField.y = 10;
            _vehicleField.x = 18;
            _vehicleField.y = 34;
            _percentField.x = 18;
            _percentField.y = 54;
            _nextField.x = 18;
            _nextField.y = 94;
            _statsField.x = 18;
            _statsField.y = 112;
            _targetsField.x = 18;
            _targetsField.y = 130;
            _battlesField.x = 18;
            _battlesField.y = height - 18;

            var chipWidth:Number = (width - 36 - CHIP_GAP * 2) / 3;
            _masteryField.width = chipWidth - 12;
            _wn8Field.width = chipWidth - 12;
            _winrateField.width = chipWidth - 12;

            _masteryField.x = 18 + 6;
            _wn8Field.x = 18 + chipWidth + CHIP_GAP + 6;
            _winrateField.x = 18 + (chipWidth + CHIP_GAP) * 2 + 6;
            _masteryField.y = 146;
            _wn8Field.y = _masteryField.y;
            _winrateField.y = _masteryField.y;
        }

        private function render() : void
        {
            if (_data == null || _cfg == null)
            {
                return;
            }
            if (_headerField == null || _vehicleField == null || _percentField == null || _nextField == null || _statsField == null
                || _targetsField == null || _masteryField == null || _wn8Field == null || _winrateField == null || _battlesField == null)
            {
                return;
            }

            _headerField.htmlText = toHtml(_data.headerHtml);
            _vehicleField.htmlText = toHtml(_data.vehicleHtml);
            _percentField.htmlText = toHtml(_data.percentHtml);
            _nextField.htmlText = toHtml(_data.nextHtml);
            _statsField.htmlText = toHtml(_data.statsHtml);

            var targetsHtml:String = toHtml(_data.targetsHtml);
            _targetsField.htmlText = targetsHtml;
            _targetsField.visible = targetsHtml.length > 0;

            _masteryField.htmlText = toHtml(_data.masteryHtml);
            _wn8Field.htmlText = toHtml(_data.wn8Html);
            _winrateField.htmlText = toHtml(_data.winrateHtml);
            _battlesField.htmlText = toHtml(_data.battlesHtml);

            drawChips();
            updateStars(Number(_data.damageRating || 0));
        }

        private function toHtml(value:*) : String
        {
            if (value === null || value === undefined)
            {
                return "";
            }
            return String(value);
        }

        private function drawChips() : void
        {
            var width:Number = Number(_cfg.width || 360);
            var chipWidth:Number = (width - 36 - CHIP_GAP * 2) / 3;
            var chipY:Number = _masteryField.y - 6;
            var chipAlpha:Number = 0.92;
            var fill:uint = mixColor(uint(_cfg.backgroundColor || 0x101114), parseColor(String(_cfg.accentSoftColor || "#3A2B17")), 0.35);
            var outline:uint = parseColor(String(_cfg.outlineColor || "#2B2D33"));

            _chipLayer.graphics.clear();
            drawChip(_masteryField.x - 6, chipY, chipWidth, CHIP_HEIGHT + 4, fill, outline, chipAlpha);
            drawChip(_wn8Field.x - 6, chipY, chipWidth, CHIP_HEIGHT + 4, fill, outline, chipAlpha);
            drawChip(_winrateField.x - 6, chipY, chipWidth, CHIP_HEIGHT + 4, fill, outline, chipAlpha);
        }

        private function drawChip(x:Number, y:Number, width:Number, height:Number, fill:uint, outline:uint, alpha:Number) : void
        {
            _chipLayer.graphics.lineStyle(1, outline, 1);
            _chipLayer.graphics.beginFill(fill, alpha);
            drawRoundRect(_chipLayer.graphics, x, y, width, height, 12);
            _chipLayer.graphics.endFill();
        }

        private function updateStars(percent:Number) : void
        {
            if (_cfg == null)
            {
                return;
            }
            var thresholds:Array = [65.0, 85.0, 95.0];
            var colors:Array = [
                parseColor(String(_cfg.starColor65 || "#60FF00")),
                parseColor(String(_cfg.starColor85 || "#02C9B3")),
                parseColor(String(_cfg.starColor95 || "#D042F3"))
            ];
            var muted:uint = parseColor(String(_cfg.mutedColor || "#8E949F"));
            var transition:Number = Number(_cfg.starAnimationWindow || 5.0);
            var starY:Number = 62;
            var starX:Number = Number(_cfg.width || 360) - 108;

            for (var i:int = 0; i < _stars.length; i++)
            {
                var ratio:Number = clamp((percent - (Number(thresholds[i]) - transition)) / transition, 0, 1);
                var color:uint = mixColor(muted, uint(colors[i]), ratio);
                var scale:Number = 0.88 + ratio * 0.18;
                drawStar(_stars[i], color, 0.25 + ratio * 0.75, scale);
                _stars[i].x = starX + i * 30;
                _stars[i].y = starY;
            }
        }

        private function drawStar(target:Sprite, color:uint, alpha:Number, scale:Number) : void
        {
            target.graphics.clear();
            target.graphics.lineStyle(1, 0xFFFFFF, 0.1);
            target.graphics.beginFill(color, alpha);

            var outer:Number = 10 * scale;
            var inner:Number = 4.8 * scale;
            var angle:Number = -Math.PI / 2;
            var step:Number = Math.PI / 5;
            var points:Array = [];
            for (var i:int = 0; i < 10; i++)
            {
                var radius:Number = (i % 2 == 0) ? outer : inner;
                points.push(new Point(Math.cos(angle) * radius, Math.sin(angle) * radius));
                angle += step;
            }

            target.graphics.moveTo(points[0].x, points[0].y);
            for each (var point:Point in points)
            {
                target.graphics.lineTo(point.x, point.y);
            }
            target.graphics.endFill();
        }

        private function updateVisibility() : void
        {
            if (_container != null && _cfg != null)
            {
                _container.visible = Boolean(_cfg.visible);
            }
        }

        private function updateDragMode() : void
        {
            if (_container == null || _cfg == null)
            {
                return;
            }
            removeDragListeners();
            if (!Boolean(_cfg.locked))
            {
                _container.buttonMode = true;
                _container.addEventListener(MouseEvent.MOUSE_DOWN, onMouseDown, false, 0, true);
            }
            else
            {
                _container.buttonMode = false;
            }
        }

        private function removeDragListeners() : void
        {
            if (_container != null)
            {
                _container.removeEventListener(MouseEvent.MOUSE_DOWN, onMouseDown);
            }
            if (stage != null)
            {
                stage.removeEventListener(MouseEvent.MOUSE_UP, onMouseUp);
            }
        }

        private function onMouseDown(event:MouseEvent) : void
        {
            if (Boolean(_cfg.locked))
            {
                return;
            }
            _dragging = true;
            _container.startDrag();
            if (stage != null)
            {
                stage.addEventListener(MouseEvent.MOUSE_UP, onMouseUp, false, 0, true);
            }
        }

        private function onMouseUp(event:MouseEvent) : void
        {
            if (!_dragging)
            {
                return;
            }
            _dragging = false;
            _container.stopDrag();
            if (stage != null)
            {
                stage.removeEventListener(MouseEvent.MOUSE_UP, onMouseUp);
            }
            if (py_savePosition != null)
            {
                py_savePosition(resolveConfigX(_container.x), resolveConfigY(_container.y));
            }
        }

        private function positionContainer() : void
        {
            if (_container == null || _cfg == null)
            {
                return;
            }
            _container.x = resolveAbsoluteX();
            _container.y = resolveAbsoluteY();
        }

        private function resolveAbsoluteX() : Number
        {
            var width:Number = Number(_cfg.width || 360);
            var x:Number = Number(_cfg.x || 0);
            switch (String(_cfg.alignX || "left"))
            {
                case "right":
                    return App.appWidth + x - width;
                case "center":
                    return App.appWidth * 0.5 + x - width * 0.5;
                default:
                    return x;
            }
        }

        private function resolveAbsoluteY() : Number
        {
            var height:Number = Number(_cfg.height || 188);
            var y:Number = Number(_cfg.y || 0);
            switch (String(_cfg.alignY || "top"))
            {
                case "bottom":
                    return App.appHeight + y - height;
                case "center":
                    return App.appHeight * 0.5 + y - height * 0.5;
                default:
                    return y;
            }
        }

        private function resolveConfigX(absoluteX:Number) : Number
        {
            var width:Number = Number(_cfg.width || 360);
            switch (String(_cfg.alignX || "left"))
            {
                case "right":
                    return absoluteX - App.appWidth + width;
                case "center":
                    return absoluteX - App.appWidth * 0.5 + width * 0.5;
                default:
                    return absoluteX;
            }
        }

        private function resolveConfigY(absoluteY:Number) : Number
        {
            var height:Number = Number(_cfg.height || 188);
            switch (String(_cfg.alignY || "top"))
            {
                case "bottom":
                    return absoluteY - App.appHeight + height;
                case "center":
                    return absoluteY - App.appHeight * 0.5 + height * 0.5;
                default:
                    return absoluteY;
            }
        }

        private function drawRoundRect(graphics:*, x:Number, y:Number, width:Number, height:Number, radius:Number) : void
        {
            graphics.drawRoundRect(x, y, width, height, radius, radius);
        }

        private function getContainer(containerName:String) : ISimpleManagedContainer
        {
            return App.containerMgr ? App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(containerName)) : null;
        }

        private function parseColor(value:String) : uint
        {
            return uint(parseInt(value.replace("#", "0x")));
        }

        private function clamp(value:Number, minimum:Number, maximum:Number) : Number
        {
            return Math.max(minimum, Math.min(maximum, value));
        }

        private function mixColor(from:uint, to:uint, ratio:Number) : uint
        {
            var r:uint = uint(((from >> 16) & 0xFF) + ((((to >> 16) & 0xFF) - ((from >> 16) & 0xFF)) * ratio));
            var g:uint = uint(((from >> 8) & 0xFF) + ((((to >> 8) & 0xFF) - ((from >> 8) & 0xFF)) * ratio));
            var b:uint = uint((from & 0xFF) + (((to & 0xFF) - (from & 0xFF)) * ratio));
            return (r << 16) | (g << 8) | b;
        }
    }
}
