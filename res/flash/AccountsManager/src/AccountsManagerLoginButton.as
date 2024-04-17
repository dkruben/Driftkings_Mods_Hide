package
{
	import flash.display.DisplayObject;
	import flash.display.DisplayObjectContainer;
	import flash.display.MovieClip;
	import flash.events.Event;
	import flash.events.TextEvent;
	import flash.utils.getQualifiedClassName;
	//
	import net.wg.gui.components.containers.MainViewContainer;
	import net.wg.gui.login.impl.LoginPage;
	import net.wg.gui.login.impl.views.SimpleForm;
	import net.wg.infrastructure.base.AbstractView;
	import net.wg.infrastructure.interfaces.IManagedContent;
	import net.wg.infrastructure.interfaces.ISimpleManagedContainer;
	import net.wg.infrastructure.managers.impl.ContainerManagerBase;
	import net.wg.data.Aliases;
	import net.wg.data.constants.generated.LAYER_NAMES;
	import net.wg.infrastructure.interfaces.IView;
	import net.wg.infrastructure.events.LoaderEvent;
	//
	import components.AMButton;

   
   public class AccountsManagerLoginButton extends AbstractView
    {
		public var py_log:Function;
		public var py_openAccMngr:Function;
		public var py_getTranslate:Function;
		
		private var isLobby:Boolean = false;
		private var amBtn:AMButton;
		private var _login:LoginPage;
		private var _form:SimpleForm;

		public function AccountsManagerLoginButton()
		{
			App.instance.loaderMgr.loadLibraries(Vector.<String>(["guiControlsLobbyBattle.swf"]));
			super();
		}

		public function as_populateLogin() : void
		{
			try
			{
				this.isLobby = false;
				this._login = this.recursiveFindDOC(DisplayObjectContainer(stage),"LoginPageUI") as LoginPage;
				this._form = this.recursiveFindDOC(DisplayObjectContainer(stage),"LoginFormUI") as SimpleForm;
				if(this._login != null)
				{
					this.amBtn = new AMButton();
					this.amBtn.tooltip = this.py_getTranslate().tooltip_l10n;
					this._login.addChild(this.amBtn);
					addEventListener(Event.RESIZE,this.resize);
					this.amBtn.addEventListener(TextEvent.LINK,this.handleAMButtonClick);
					this.resize();
				}
				return;
			}
			catch(err:Error)
			{
				py_log("as_populateLogin " + err.getStackTrace());
				return;
			}
		}
		
		public function as_populateLobby() : void
		{
			this.isLobby = true;
		}
		
		private function resize(event:Event = null) : void
		{
			var e:Event = event;
			if(!this.isLobby)
			{
				try
				{
					this.amBtn.x = this._form.parent.x + this._form.keyboardLang.x;
					this.amBtn.y = this._form.parent.y + this._form.submit.y;
					return;
				}
				catch(err:Error)
				{
					py_log("resize " + err.getStackTrace());
					return;
				}
			}
			else
			{
				return;
			}
		}

		private function handleAMButtonClick(e:TextEvent) : void
		{
			this.py_openAccMngr();
		}
		
		override protected function nextFrameAfterPopulateHandler() : void
		{
			if(parent != App.instance)
			{
				(App.instance as MovieClip).addChild(this);
			}
		}
		
		override protected function configUI() : void 
		{
			super.configUI();

			// process already loaded views
			var viewContainer:MainViewContainer = _getContainer(LAYER_NAMES.VIEWS) as MainViewContainer;
			if (viewContainer != null)
			{
				var num:int = viewContainer.numChildren;
				for (var idx:int = 0; idx < num; ++idx)
				{
					var view:IView = viewContainer.getChildAt(idx) as IView;
					if (view != null)
					{
						processView(view);
					}
				}
				var topmostView:IManagedContent = viewContainer.getTopmostView();
				if (topmostView != null)
				{
					viewContainer.setFocusedView(topmostView);
				}
			}

			// subscribe to stage resize
			App.instance.stage.addEventListener(Event.RESIZE, resize);

			// subscribe to container manager loader
			(App.containerMgr as ContainerManagerBase).loader.addEventListener(LoaderEvent.VIEW_LOADED, onViewLoaded, false, 0, true);
		}

		
		private function _getContainer(containerName:String) : ISimpleManagedContainer
		{
			return App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(containerName))
		}

		
		private function onViewLoaded(event:LoaderEvent) : void 
		{
			var view:IView = event.view as IView;
			processView(view);
		}

		
		private function processView(view:IView) : void 
		{
			var alias:String = view.as_config.alias;
			try
			{
				if (alias == Aliases.LOGIN)
				{
					this.isLobby = false;
					this._login = view as LoginPage;
				}
				if (alias == Aliases.LOBBY)
				{
				    this.isLobby = true;

				}
			}
			catch (err:Error)
			{
				py_log("processView " + err.getStackTrace());
			}
		}

		private function recursiveFindDOC(doc:DisplayObjectContainer, text:String) : DisplayObjectContainer
		{
			var object:DisplayObject = null;
			var child:DisplayObjectContainer = null;
			var num:int = 0;
			var showObj:DisplayObjectContainer = null;
			while(num < doc.numChildren)
			{
				object = doc.getChildAt(num);
				if(object is DisplayObject && getQualifiedClassName(object) == text)
				{
					showObj = object as DisplayObjectContainer;
				}
				if(showObj != null)
				{
					return showObj;
				}
				if((Boolean(child = object as DisplayObjectContainer)) && child.numChildren > 0)
				{
					showObj = this.recursiveFindDOC(child ,text);
				}
				num++;
			}
			return showObj;
		}
	}
}