package driftkings
{
   import driftkings.views.battle.DispersionTimerUI;
   import mods.common.AbstractViewInjector;
   
   public class DispersionTimerInjector extends AbstractViewInjector
   {
	
	   public function DispersionTimerInjector()
		{
			super();
		}
		
		override protected function onPopulate() : void
		{
			autoDestroy = false;
			componentName = "DispersionTimerView";
			componentUI = DispersionTimerUI;
			super.onPopulate();
		}
	}
}