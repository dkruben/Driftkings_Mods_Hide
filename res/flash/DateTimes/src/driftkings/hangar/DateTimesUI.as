package driftkings.hangar
{
	import flash.display.MovieClip;
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	import net.wg.data.Aliases;
	import net.wg.data.constants.generated.LAYER_NAMES;
	import net.wg.gui.components.containers.MainViewContainer;
	import net.wg.infrastructure.base.AbstractView;
	import net.wg.infrastructure.events.LifeCycleEvent;
	import net.wg.infrastructure.events.LoaderEvent;
	import net.wg.infrastructure.interfaces.IManagedContent;
	import net.wg.infrastructure.interfaces.ISimpleManagedContainer;
	import net.wg.infrastructure.interfaces.IView;
	import net.wg.infrastructure.managers.impl.ContainerManagerBase;
	import driftkings.hangar.utils.Filters;
	import driftkings.hangar.utils.TextExt;
   
	public class DateTimesUI extends AbstractView
	{
		private var dateTime:TextExt;
		private var config:Object;

		public function DateTimesUI()
		{
			super();
			this.tabEnabled = false;
			this.tabChildren = false;
			this.mouseEnabled = false;
			this.mouseChildren = false;
			this.buttonMode = false;
			this.addEventListener(Event.RESIZE, this._onResizeHandle);
		}
      
		override protected function configUI() : void
		{
			var num:int = 0;
			var idx:int = 0;
			var topmostView:IManagedContent = null;
			var view:IView = null;
			super.configUI();
			var viewContainer:MainViewContainer = this._getContainer(LAYER_NAMES.VIEWS) as MainViewContainer;
			if(viewContainer != null)
			{
				num = viewContainer.numChildren;
				for(idx = 0; idx < num; idx++)
				{
					view = viewContainer.getChildAt(idx) as IView;
					if(view != null)
					{
						this.processView(view);
					}
				}
				topmostView = viewContainer.getTopmostView();
				if(topmostView != null)
				{
					viewContainer.setFocusedView(topmostView);
				}
			}
			(App.containerMgr as ContainerManagerBase).loader.addEventListener(LoaderEvent.VIEW_LOADED,this.onViewLoaded,false,0,true);
		}

		private function onViewLoaded(event:LoaderEvent) : void
		{
			var view:IView = event.view as IView;
			this.processView(view);
		}

		private function processView(view:IView) : void
		{
			if (view.as_config.alias == Aliases.LOBBY)
			{
				view.addChild(this.dateTime);
			}
		}

		override protected function nextFrameAfterPopulateHandler() : void
		{
			super.nextFrameAfterPopulateHandler();
			this.addAsChildToApp();
		}

		public function addAsChildToApp() : void
		{
			if(parent != App.instance)
			{
				(App.instance as MovieClip).addChild(this);
			}
		}

		private function _getContainer(containerName:String) : ISimpleManagedContainer
		{
			return App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(containerName));
		}
      
		override protected function onDispose() : void
		{
			(App.containerMgr as ContainerManagerBase).loader.removeEventListener(LoaderEvent.VIEW_LOADED,this.onViewLoaded);
			this.removeEventListener(Event.RESIZE, this._onResizeHandle);
			this.as_clearScene();
			super.onDispose();
		}
		
		public function as_clearScene():void
		{
			while (this.numChildren > 0)
			{
				this.removeChildAt(0);
			}
			this.dateTime = null;
			App.utils.data.cleanupDynamicObject(this.config);
		}
		
		public function as_startUpdateLobby(settings:Object):void
		{
			this.as_clearScene();
			if (settings.enabled)
			{
				this.config = settings;
				this.x = settings.lobbyPos.x < 0 ? parent.width + settings.lobbyPos.x : settings.lobbyPos.x
				this.y = settings.lobbyPos.y < 0 ? parent.height + settings.lobbyPos.y : settings.lobbyPos.y
				this.dateTime = new TextExt(settings.lobbyPos.x, settings.lobbyPos.y, TextFieldAutoSize.CENTER, this);
			}
		}
		
		public function as_creditCalcLobby(text:String):void
		{
			if (this.dateTime)
			{
				this.dateTime.htmlText = text;
			}
		}
		
		public function _onResizeHandle(event:Event):void
		{
			this.x = this.config.lobbyPos.x < 0 ? parent.width + this.config.lobbyPos.x : this.config.lobbyPos.x
			this.y = this.config.lobbyPos.y < 0 ? parent.height + this.config.lobbyPos.y : this.config.lobbyPos.y
		}
	}
}