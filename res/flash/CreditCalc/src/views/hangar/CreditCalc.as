package views.hangar
{
	import flash.display.MovieClip;
	import flash.display.Sprite;
	import flash.events.MouseEvent;
	import flash.filters.DropShadowFilter;
	import flash.text.TextField;
	import net.wg.data.constants.generated.LAYER_NAMES;
	import net.wg.gui.components.containers.MainViewContainer;
	import net.wg.data.Aliases;
	import net.wg.infrastructure.base.AbstractView;
	import net.wg.infrastructure.events.LoaderEvent;
	import net.wg.infrastructure.interfaces.IManagedContent;
	import net.wg.infrastructure.interfaces.ISimpleManagedContainer;
	import net.wg.infrastructure.interfaces.IView;
	import net.wg.infrastructure.managers.impl.ContainerManagerBase;

	public class CreditCalc extends AbstractView
	{
		private static const BACKGROUND_WIDTH:int = 400;
		private static const BACKGROUND_HEIGHT:int = 150;
		private static const INITIAL_X_OFFSET:int = 400;
		private static const INITIAL_Y_OFFSET:int = 35;

		private var _isDragging:Boolean = false;
		private var _textField:TextField;
		private var _background:MovieClip;
		private var _container:Sprite;

		public var py_log:Function;

		public function CreditCalc()
		{
			super();
		}

		override protected function onPopulate() : void
		{
			super.onPopulate();
		}

		override protected function onDispose() : void
		{
			cleanUpEventListeners();
			super.onDispose();
		}

		public function as_setText(text:String) : void
		{
			try
			{
				_textField.htmlText = text;
				_background.width = _textField.textWidth + 20;
				_background.height = _textField.textHeight + 20;
			}
			catch(e:Error)
			{
				handleError("[CreditCalc] as_setText: ", e);
			}
		}

		public function as_setPosition(x:int, y:int):void
		{
			if (_container)
			{
				try
				{
					_container.x = x;
					_container.y = y;
				}
				catch(e:Error)
				{
					handleError("[CreditCalc] as_setPosition: ", e);
				}
			}
		}

		public function as_setBackground(isEnabled:Boolean, color:String, alpha:Number) : void
		{
			try
			{
        		var colorNum:Number = parseInt(color.replace("#", "0x"));
				_background.visible = isEnabled;
				_background.graphics.clear();
				_background.graphics.beginFill(colorNum, alpha);
				_background.graphics.drawRect(0, 0, _textField.width, _textField.height);
				_background.graphics.endFill();
			}
			catch(e:Error)
			{
				handleError("[CreditCalc] as_setBackground: ", e);
			}
		}

		override protected function configUI() : void
		{
			super.configUI();
			initializeUIComponents();
			addEventListeners();
		}

		private function initializeUIComponents():void
		{
			var viewContainer:MainViewContainer = getContainer(LAYER_NAMES.VIEWS) as MainViewContainer;
			if (viewContainer != null)
			{
				var view:IView;
				for (var idx:int = 0; idx < viewContainer.numChildren; idx++)
				{
					view = viewContainer.getChildAt(idx) as IView;
					if (view != null)
					{
						processView(view);
					}
				}
			}
		}

		private function addEventListeners():void
		{
			if (App.containerMgr)
			{
				(App.containerMgr as ContainerManagerBase).loader.addEventListener(LoaderEvent.VIEW_LOADED, onViewLoaded, false, 0, true);
			}
		}

		private function onViewLoaded(event:LoaderEvent) : void
		{
			var view:IView = event.view as IView;
			if (view)
			{
				processView(view);
			}
		}

		private function processView(view:IView) : void
		{
			if(view && view.as_config && view.as_config.alias == Aliases.LOBBY_HANGAR)
			{
				initTextField();
				initBackground();
				createContainer();
				addChildToView(view);
			}
		}

		private function initTextField():void
		{
			_textField = new TextField();
			_textField.autoSize = "left";
			_textField.multiline = true;
			_textField.wordWrap = true;
			_textField.width = BACKGROUND_WIDTH;
			_textField.height = BACKGROUND_HEIGHT;
			_textField.selectable = false;
			applyTextFilters();
		}

		private function applyTextFilters():void
		{
			var filter:DropShadowFilter = new DropShadowFilter(5, 90, 0, 1, 5, 5);
			_textField.filters = [filter];
		}

		private function initBackground():void
		{
			_background = new MovieClip();
			_background.name = "background";
			_background.visible = false;
			resetBackgroundGraphics();
		}

		private function resetBackgroundGraphics():void
		{
			_background.graphics.clear();
			_background.graphics.beginFill(0, 0);
			_background.graphics.drawRect(0, 0, BACKGROUND_WIDTH, BACKGROUND_HEIGHT);
			_background.graphics.endFill();
		}

		private function createContainer():void
		{
			_container = new Sprite();
			_container.addChild(_background);
			_container.addChild(_textField);
			_container.x = (App.appWidth + INITIAL_X_OFFSET) / 2;
			_container.y = INITIAL_Y_OFFSET;
			addMouseListeners();
		}

		private function addMouseListeners():void
		{
			_container.addEventListener(MouseEvent.MOUSE_DOWN, handleMouseDown);
			_container.addEventListener(MouseEvent.MOUSE_UP, handleMouseUp);
			_container.addEventListener(MouseEvent.MOUSE_MOVE, handleMouseMove);
		}

		private function addChildToView(view:IView):void
		{
			if (view && _container)
			{
				view.addChild(_container);
			}
		}

		private function handleMouseDown(event:MouseEvent) : void
		{
			_isDragging = true;
			_container.startDrag();
		}

		private function handleMouseMove(event:MouseEvent) : void
		{}

		private function handleMouseUp(event:MouseEvent) : void
		{
			if(_isDragging)
			{
				_isDragging = false;
				_container.stopDrag();
			}
		}

		private function handleError(message:String, error:Error):void
		{
			if (DebugUtils)
			{
				py_log(message + error.name);
				py_log(error.getStackTrace());
			}
		}

		private function cleanUpEventListeners():void
		{
			if (_container)
			{
				_container.removeEventListener(MouseEvent.MOUSE_DOWN, handleMouseDown);
				_container.removeEventListener(MouseEvent.MOUSE_UP, handleMouseUp);
				_container.removeEventListener(MouseEvent.MOUSE_MOVE, handleMouseMove);
			}

			if (App.containerMgr)
			{
				(App.containerMgr as ContainerManagerBase).loader.removeEventListener(LoaderEvent.VIEW_LOADED, onViewLoaded);
			}
		}

		private function getContainer(containerName:String) : ISimpleManagedContainer
		{
			return App.containerMgr ? App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(containerName)) : null;
		}
	}
}