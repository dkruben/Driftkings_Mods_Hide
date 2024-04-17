package
{
	import components.AM_MODES;
	import net.wg.gui.components.controls.*;
	import net.wg.infrastructure.base.*;
	import scaleform.clik.data.*;
	import scaleform.clik.events.*;
   
	public class AccountsManagerWindow extends AbstractWindowView
    {
		private static const ACTION_ADD_ACCOUNT:String = "add";
     	private static const ACTION_EDIT_ACCOUNT:String = "edit";
       
		public var py_get_clusters:Function;
		public var py_getTranslate:Function;
		public var py_setAddAccount:Function;
		public var py_setEditAccount:Function;
		
		private var langData:Object;
		private var modeType:String;
		private var submitBtn:SoundButton;
		private var cancelBtn:SoundButton;
		private var showPswd:CheckBox;
		private var titleLabel:TextFieldShort;
		private var emailLabel:TextFieldShort;
		private var passwordLabel:TextFieldShort;
		private var clusterLabel:TextFieldShort;
		private var titleVal:TextInput;
		private var loginVal:TextInput;
		private var passwordVal:TextInput;
		private var clusterVal:DropdownMenu;
		private var qweid:String;

        public function AccountsManagerWindow()
        {
            super();
            isCentered = true;
        }

		private function handleSubmitBtnClick(e:ButtonEvent) : void
		{
			if(this.titleVal.text == "")
			{
				this.titleVal.highlight = true;
				return;
			}
			if(!this.isValidEmail(this.loginVal.text))
			{
				this.loginVal.highlight = true;
				return;
			}
			if(this.modeType == ACTION_ADD_ACCOUNT)
			{
				this.py_setAddAccount(this.titleVal.text,this.loginVal.text,this.passwordVal.text,this.clusterVal.selectedIndex);
			}
			else if(this.modeType == ACTION_EDIT_ACCOUNT)
			{
				this.py_setEditAccount(this.qweid,this.titleVal.text,this.loginVal.text,this.passwordVal.text,this.clusterVal.selectedIndex);
			}
		}

        private function handleCancelBtnClick(e:ButtonEvent):void
        {
            onWindowClose();
        }

        private function handleShowPswdClick(e:ButtonEvent):void
        {
            passwordVal.displayAsPassword = !this.passwordVal.displayAsPassword;
        }

        public function as_setEditAccountData(id:String, title:String, email:String, password:String, cluster:int):void
        {
			this.qweid = id;
			this.titleVal.text = title;
			this.loginVal.text = email;
			this.passwordVal.text = password;
			this.clusterVal.selectedIndex = cluster;
            clusterVal.selectedIndex = cluster;
            this.modeType = ACTION_EDIT_ACCOUNT;
        }

        public function as_setAddAccount():void
        {
            this.modeType = ACTION_ADD_ACCOUNT;
        }

		override protected function onPopulate() : void
		{
			var dp:Array = null;
			super.onPopulate();
			this.langData = this.py_getTranslate();
			window.title = this.langData.window_title_l10n;
			window.setTitleIcon("team");
			width = 340;
			height = 200;
			try
			{
				this.titleLabel = addChild(App.utils.classFactory.getComponent("TextFieldShort", TextFieldShort, {"label":this.langData.nick_l10n, "selectable":false,	"showToolTip":false, "x":5, "y":10})) as TextFieldShort;
				this.titleVal = addChild(App.utils.classFactory.getComponent("TextInput", TextInput, {"width":210, "x":60, "y":5})) as TextInput;
				this.emailLabel = addChild(App.utils.classFactory.getComponent("TextFieldShort",TextFieldShort,{"label":"Email:", "selectable":false, "showToolTip":false, "x":5, "y":40})) as TextFieldShort;
				this.loginVal = addChild(App.utils.classFactory.getComponent("TextInput",TextInput,{"width":210,"x":60,"y":35})) as TextInput;
				this.passwordLabel = addChild(App.utils.classFactory.getComponent("TextFieldShort",TextFieldShort,{"label":this.langData.password_l10n,"selectable":false,"showToolTip":false,"x":5,"y":70})) as TextFieldShort;
				this.passwordVal = addChild(App.utils.classFactory.getComponent("TextInput",TextInput,{"displayAsPassword":true,"width":210,"x":60,"y":65})) as TextInput;
				this.showPswd = addChild(App.utils.classFactory.getComponent("CheckBox",CheckBox,{"label":this.langData.show_password_l10n,"visible":true,"x":60,"y":95})) as CheckBox;
				this.showPswd.addEventListener(ButtonEvent.CLICK,this.handleShowPswdClick);
				this.clusterLabel = addChild(App.utils.classFactory.getComponent("TextFieldShort",TextFieldShort,{"label":this.langData.server_l10n,"selectable":false,"showToolTip":false,"x":5,"y":125})) as TextFieldShort;
				dp = this.py_get_clusters();
				this.clusterVal = addChild(App.utils.classFactory.getComponent("DropdownMenuUI",DropdownMenu,{"rowCount":10,"width":210,"x":60,"y":120,"menuDirection":"down","itemRenderer":"DropDownListItemRendererSound","dropdown":"DropdownMenu_ScrollingList","dataProvider":new DataProvider(dp),"selectedIndex":0})) as DropdownMenu;
				this.submitBtn = addChild(App.utils.classFactory.getComponent("ButtonNormal",SoundButton,{"label":this.langData.save_l10n,"width":100,"x":120, "y":165})) as SoundButton;
				this.submitBtn.addEventListener(ButtonEvent.CLICK,this.handleSubmitBtnClick);
				this.cancelBtn = addChild(App.utils.classFactory.getComponent("ButtonBlack", SoundButton,{"label":this.langData.cancel_l10n, "width":100, "x":230, "y":165})) as SoundButton;
				this.cancelBtn.addEventListener(ButtonEvent.CLICK,this.handleCancelBtnClick);
			}
			catch(err:Error)
			{
				DebugUtils.LOG_ERROR(err.getStackTrace());
			}
		}

        private function isValidEmail(email:String):Boolean
        {
            var emailExpression:RegExp = /([a-zA-Z0-9._-]+?)@([a-zA-Z0-9.-]+)\.([a-zA-Z]{2,4})/;
            return emailExpression.test(email);
        }
    }
}