package driftkings.injector
{
	import net.wg.gui.battle.components.BattleUIDisplayable;
	import net.wg.gui.battle.views.BaseBattlePage;
   
	public class BattleDisplayable extends BattleUIDisplayable
	{
		public var battlePage:BaseBattlePage;
		public var componentName:String;
      
		public function BattleDisplayable()
		{
			super();
		}
      
		public function initBattle() : void
		{
			if(!this.battlePage.contains(this))
			{
				this.battlePage.addChildAt(this,1);
			}
			if(!this.battlePage.isFlashComponentRegisteredS(this.componentName))
			{
				this.battlePage.registerFlashComponent(this,this.componentName);
			}
		}
      
		public function finiBattle() : void
		{
			if(this.battlePage.isFlashComponentRegisteredS(this.componentName))
			{
				this.battlePage.unregisterFlashComponentS(this.componentName);
			}
			if(this.battlePage.contains(this))
			{
				this.battlePage.removeChild(this);
			}
		}
      
		override protected function onPopulate() : void
		{
			super.onPopulate();
		}
      
		override protected function onDispose() : void
		{
			this.finiBattle();
			super.onDispose();
		}
	}
}