package driftkings
{
   import driftkings.views.battle.OwnHealthUI;
   import mods.common.AbstractViewInjector;

   public class OwnHealthInjector extends AbstractViewInjector
   {
	   public function OwnHealthInjector()
		{
			super();
		}

		override protected function onPopulate() : void
		{
			autoDestroy = false;
			componentName = "OwnHealthView";
			componentUI = OwnHealthUI;
			super.onPopulate();
		}
	}
}