package
{
   import components.*;
   import flash.display.*;
   import flash.events.*;
   import flash.text.*;
   import flash.utils.*;
   import net.wg.gui.components.controls.*;
   import net.wg.gui.login.impl.views.*;
   import net.wg.infrastructure.base.*;
   import scaleform.clik.events.*;

    public class AccountsManager extends AbstractWindowView
    {
		public var py_log:Function;
		public var callFromFlash:Function;
		public var py_getTranslate:Function;
		public var py_setLoginDataById:Function;
		public var py_openAddAccountWindow:Function;
		private var langData:Object;
		private var accountsList:TextField;
		private var newAccButton:SoundButton;
		private var autoEnterCheckBox:CheckBox;
		private var _form:SimpleForm;
			
		public function AccountsManager()
		{
			super();
			isCentered = true;
		}

		public function as_callToFlash(data_array:Array) : void
		{
			var htmlText:String = null;
			var data:Object = null;
			var data_arr:Array = data_array;
			try
			{
				htmlText = "";
				for each(data in data_arr)
				{
					htmlText += "<font size=\'17\' color=\'#FFFFFF\'>" + data.user + "<br />" + "<img src=\'img://gui/maps/icons/library/BattleResultIcon-1.png\'> " + data.cluster + "</font><br />" + "<a href=\'event:0_" + data.id + "\'>" + this.langData.submit_l10n + "</a>    " + "<a href=\'event:1_" + data.id + "\'>" + this.langData.edit_l10n + "</a>    " + "<a href=\'event:2_" + data.id + "\'>" + this.langData.delete_l10n + "</a><br />" + "<img width=\'" + this.accountsList.width.toString() + "\' src=\'img://gui/flash/AccountsManager/splitter.png\'><br /><br />";
				}
				this.accountsList.htmlText = htmlText;
				return;
			}
			catch(err:Error)
			{
				py_log("as_callToFlash " + err.message);
				return;
			}
		}

        public function handleLinkClick(e:TextEvent):void
        {
            var action: String = e.text.charAt(0);
            var id: String = e.text.substring(2);

            switch (e.text.charAt(0))
            {
                case "0":
                    action = AM_MODES.SUBMIT;
                    break;
                case "1":
                    action = AM_MODES.EDIT;
                    break;
                case "2":
                    action = AM_MODES.DELETE;
                    break;
            }

            if (action == "submit")
            {
                py_setLoginDataById(id, _form);
                if (autoEnterCheckBox.selected)
				{
                    _form.submit.dispatchEvent(new ButtonEvent(ButtonEvent.CLICK));
                }
            }
			else
			{
			callFromFlash({"action": action, "id": id});
            }
        }

        public function handleAddButtonClick(e:ButtonEvent):void
        {
            py_openAddAccountWindow();
        }

		override protected function onPopulate() : void
		{
			super.onPopulate();
			this._form = this.recursiveFindDOC(DisplayObjectContainer(stage),"LoginFormUI") as SimpleForm;
			this.langData = this.py_getTranslate();
			window.title = this.langData.window_title_l10n;
			width = 340;
			height = 530;
			try
			{
				this.accountsList = new TextField();
				this.accountsList.x = 10;
				this.accountsList.y = 10;
				this.accountsList.width = 320;
				this.accountsList.height = 490;
				this.accountsList.multiline = true;
				this.accountsList.selectable = false;
				this.accountsList.htmlText = "";
				addChild(this.accountsList);
				this.accountsList.addEventListener(TextEvent.LINK,this.handleLinkClick);
				this.newAccButton = addChild(App.utils.classFactory.getComponent("ButtonNormal",SoundButton,{"label":this.langData.add_l10n,"width":100,"x":122,"y":500})) as SoundButton;
				this.autoEnterCheckBox = addChild(App.utils.classFactory.getComponent("CheckBox",CheckBox,{"label":this.langData.auto_enter_l10n,"x":10,"y":500,"selected":true})) as CheckBox;
				this.newAccButton.addEventListener(ButtonEvent.CLICK,this.handleAddButtonClick);
				return;
			}
			catch(err:Error)
			{
				py_log("onPopulate " + err.message);
				return;
			}
		}
		
		private function recursiveFindDOC(dOC:DisplayObjectContainer, className:String) : DisplayObjectContainer
		{
			var child:DisplayObject = null;
			var childOC:DisplayObjectContainer = null;
			var i:int = 0;
			var container:DisplayObjectContainer = null;
			while(i < dOC.numChildren)
			{
				child = dOC.getChildAt(i);
				if(child is DisplayObject && getQualifiedClassName(child) == className)
				{
					container = child as DisplayObjectContainer;
				}
				if(container != null)
				{
					return container;
				}
				if((Boolean(childOC = child as DisplayObjectContainer)) && childOC.numChildren > 0)
				{
					container = this.recursiveFindDOC(childOC, className);
				}
				i++;
			}
			return container;
		}
    }
}