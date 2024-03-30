package mods.common
{
	import net.wg.data.constants.generated.LAYER_NAMES;
	import net.wg.gui.battle.views.BaseBattlePage;
	import net.wg.gui.components.containers.MainViewContainer;
	import net.wg.infrastructure.base.AbstractView;
	import net.wg.infrastructure.interfaces.ISimpleManagedContainer;
   
	public class AbstractComponentInjector extends AbstractView
	{
		public var componentUI:Class = null;
      
		public var componentName:String = null;
      
		public var autoDestroy:Boolean = false;
      
		public var destroy:Function = null;
      
		public function AbstractComponentInjector()
		{
			super();
		}
      
		private function createComponent() : BattleDisplayable
		{
			var component:BattleDisplayable = new this.componentUI() as BattleDisplayable;
			this.configureComponent(component);
			return component;
		}
      
		protected function configureComponent(component:BattleDisplayable) : void
		{
		}
      
		override protected function onPopulate() : void
		{
			var view:BaseBattlePage = null;
			var component:BattleDisplayable = null;
			super.onPopulate();
			var mainViewContainer:MainViewContainer = MainViewContainer(App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(LAYER_NAMES.VIEWS)));
			var windowContainer:ISimpleManagedContainer = App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(LAYER_NAMES.WINDOWS));
			for(var idx:int = 0; idx < mainViewContainer.numChildren; idx++)
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
			}
			mainViewContainer.setFocusedView(mainViewContainer.getTopmostView());
			if(windowContainer != null)
			{
				windowContainer.removeChild(this);
			}
			if(this.autoDestroy)
			{
				App.utils.scheduler.scheduleOnNextFrame(function():void
				{
					destroy();
				});
			}
		}
	}
}