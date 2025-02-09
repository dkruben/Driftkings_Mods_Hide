package driftkings.views.battle
{
    import flash.filters.DropShadowFilter;
    import flash.text.TextField;
    import net.wg.data.constants.generated.LAYER_NAMES;
    import net.wg.gui.battle.random.views.BattlePage;
    import net.wg.gui.components.containers.MainViewContainer;
    import net.wg.infrastructure.base.AbstractView;
    import net.wg.infrastructure.managers.impl.ContainerManagerBase;
    import scaleform.gfx.TextFieldEx;

    public class DriftkingsPlayersPanelAPI extends AbstractView
    {
        private static const NAME_MAIN:String = "main";
        
        public static var ui:DriftkingsPlayersPanelAPI;

        private var viewPage:BattlePage;
        private var configs:Object = {};
        private var textFields:Object = {};

        public function DriftkingsPlayersPanelAPI()
        {
            super();
            ui = this;
        }

        override protected function onPopulate():void
        {
            super.onPopulate();
            initializeViewPage();
        }

        override protected function onDispose():void
        {
            cleanUpTextFields();
            viewPage = null;
            ui = null;
            configs = null;
            textFields = null;
            super.onDispose();
        }

        public function as_create(linkage:String, config:Object):void
        {
            if (!linkage || !config) return;

            if (viewPage)
            {
                configs[linkage] = config;
                textFields[linkage] = {};
            }
        }

        public function as_update(linkage:String, data:Object):void
        {
            if (viewPage && linkage in configs)
            {
                updateComponent(linkage, data);
            }
        }

        public function as_delete(linkage:String):void
        {
            if (viewPage)
            {
                delete configs[linkage];
                delete textFields[linkage];
            }
        }

        private function initializeViewPage():void
		{
			try
			{
				parent.removeChild(this);
                if (!App.containerMgr) {
                    DebugUtils.LOG_ERROR("App.containerMgr is null.");
                    return;
                }
                const containerManager:ContainerManagerBase = App.containerMgr as ContainerManagerBase;
				const viewContainer:MainViewContainer = containerManager.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(LAYER_NAMES.VIEWS)) as MainViewContainer;

				if (!viewContainer) throw new Error("MainViewContainer is null.");

				viewContainer.setFocusedView(viewContainer.getTopmostView());
				viewPage = viewContainer.getChildByName(NAME_MAIN) as BattlePage;

				if (!viewPage) throw new Error("BattlePage is not found.");
			}
			catch (error:Error)
			{
				DebugUtils.LOG_ERROR("initializeViewPage failed: " + error.message);
			}
		}

        private function updateComponent(linkage:String, data:Object):void
        {
            try
            {
                if (!textFields[linkage].hasOwnProperty(data.vehicleID) && !createTextField(linkage, data.vehicleID))
                {
                    return;
                }

                const textField:TextField = textFields[linkage][data.vehicleID];
                textField.htmlText = configs[linkage].isHtml ? data.text : data.text;
            }
            catch (error:Error)
            {
                DebugUtils.LOG_ERROR("updateComponent failed: " + error.message);
            }
        }

        private function createTextField(linkage:String, vehicleID:Object):Boolean
		{
			if (!viewPage) return false;

			const playersPanel:* = viewPage.playersPanel;
			if (!playersPanel || !playersPanel.listLeft || !playersPanel.listRight) return false;

			const isRight:Boolean = !getPlayersPanelHolder(vehicleID, playersPanel.listLeft);
			const playersPanelHolder:* = isRight ? playersPanel.listRight.getHolderByVehicleID(vehicleID) : playersPanel.listLeft.getHolderByVehicleID(vehicleID);

			if (!playersPanelHolder) return false;

			const config:Object = configs[linkage][isRight ? "right" : "left"];
			const shadow:Object = configs[linkage].shadow;

			const textField:TextField = new TextField();
			configureTextField(textField, config, shadow);

			textField.x = playersPanelHolder._listItem.vehicleIcon.x + config.x;
			textField.y = playersPanelHolder._listItem.vehicleIcon.y + config.y;

			const movieIndex:int = playersPanelHolder._listItem.getChildIndex(playersPanelHolder._listItem.vehicleTF) + 1;
			playersPanelHolder._listItem.addChildAt(textField, movieIndex);

			if (!textFields[linkage])
			{
				textFields[linkage] = {};
			}

			textFields[linkage][vehicleID] = textField;
			return true;
		}

        private function configureTextField(textField:TextField, config:Object, shadow:Object):void
        {
            textField.visible = true;
            textField.height = config.height;
            textField.width = config.width;
            textField.autoSize = config.align;
            textField.selectable = false;

            const shadowFilter:DropShadowFilter = new DropShadowFilter(shadow.distance, shadow.angle, parseInt("0x" + shadow.color.replace("#", ""), 16), shadow.alpha, shadow.blurX, shadow.blurY, shadow.strength, shadow.quality);
            textField.filters = [shadowFilter];
            TextFieldEx.setNoTranslate(textField, true);
        }

        private function getPlayersPanelHolder(vehicleID:Object, list:*):*
        {
            return list.getHolderByVehicleID(vehicleID);
        }

        private function cleanUpTextFields():void
        {
            for (var linkage:String in textFields)
            {
                for (var vehicleID:String in textFields[linkage])
                {
                    var textField:TextField = textFields[linkage][vehicleID];
                    if (textField && textField.parent)
                    {
                        textField.parent.removeChild(textField);
                    }
                }
            }
        }
    }
}