package driftkings
{
   import driftkings.views.battle.SixthSenseUI;
   import mods.common.AbstractViewInjector;
   
   public class SixthSenseInjector extends AbstractViewInjector
   {
		public function SixthSenseInjector()
		{
			super();
		}
		
		override protected function onPopulate() : void
		{
			autoDestroy = false;
			componentName = "SixthSenseView";
			componentUI = SixthSenseUI;
			super.onPopulate();
		}
	}
}