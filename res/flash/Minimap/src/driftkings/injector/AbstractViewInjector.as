package driftkings.injector
{
	import net.wg.data.constants.generated.LAYER_NAMES;
	import net.wg.gui.battle.views.BaseBattlePage;
	import net.wg.gui.components.containers.MainViewContainer;
	import net.wg.infrastructure.base.AbstractView;
	import net.wg.infrastructure.interfaces.ISimpleManagedContainer;
   
	public class AbstractViewInjector extends AbstractView
	{
		public var componentUI:Class = null;
		public var componentName:String = null;
		public var autoDestroy:Boolean = false;
		public var destroy:Function = null;
      
		public function AbstractViewInjector()
		{
			super();
		}
      
		private function createComponent() : BattleDisplayable
		{
			var component:BattleDisplayable = new this.componentUI() as BattleDisplayable;
			this.configureComponent(component);
			return component;
		}
      
		protected function configureComponent(param1:BattleDisplayable) : void
		{}
      
		override protected function onPopulate() : void
		{
			var mainViewContainer:MainViewContainer;
			var windowContainer:ISimpleManagedContainer;
			var idx:int;
			var view:BaseBattlePage = null;
			var component:BattleDisplayable = null;
			super.onPopulate();
			mainViewContainer = MainViewContainer(App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(LAYER_NAMES.VIEWS)));
			windowContainer = App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(LAYER_NAMES.WINDOWS));
			idx = 0;
			while(idx < mainViewContainer.numChildren)
			{
				view = mainViewContainer.getChildAt(idx) as BaseBattlePage;
				if(view)
				{
					component = this.createComponent();
					component.componentName = this.componentName;
					component.battlePage = view;
					component.initBattle();
					break;
				}
				idx++;
			}
			mainViewContainer.setFocusedView(mainViewContainer.getTopmostView());
			if(windowContainer != null)
			{
				windowContainer.removeChild(this);
			}
			if(this.autoDestroy)
			{
				App.utils.scheduler.scheduleOnNextFrame(function():*
				{
					destroy();
				});
			}
		}
	}
}