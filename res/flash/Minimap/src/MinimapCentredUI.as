package 
{
	import driftkings.views.battle.MinimapCentred;
	import driftkings.injector.AbstractViewInjector;
   
	public class MinimapCentredUI extends AbstractViewInjector
	{
		public function MinimapCentredUI()
		{
			super();
		}

		override protected function onPopulate() : void
		{
			autoDestroy = false;
			componentName = "MinimapCentredView";
			componentUI = MinimapCentred;
			super.onPopulate();
		}
	}
}