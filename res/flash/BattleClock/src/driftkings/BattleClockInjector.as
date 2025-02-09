package driftkings
{
   import driftkings.views.battle.BattleClockUI;
   import mods.common.AbstractViewInjector;
   
   public class BattleClockInjector extends AbstractViewInjector
   {
	
	   public function BattleClockInjector()
		{
			super();
		}
		
		override protected function onPopulate() : void
		{
			autoDestroy = false;
			componentName = "BattleClockView";
			componentUI = BattleClockUI;
			super.onPopulate();
		}
	}
}