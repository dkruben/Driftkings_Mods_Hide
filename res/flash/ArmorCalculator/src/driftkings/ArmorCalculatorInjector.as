package driftkings
{
   import driftkings.views.battle.ArmorCalculatorUI;
   import mods.common.AbstractViewInjector;
   
   public class ArmorCalculatorInjector extends AbstractViewInjector
   {
	   public function ArmorCalculatorInjector()
		{
			super();
		}

		override protected function onPopulate() : void
		{
			autoDestroy = false;
			componentName = "ArmorCalculatorView";
			componentUI = ArmorCalculatorUI;
			super.onPopulate();
		}
	}
}