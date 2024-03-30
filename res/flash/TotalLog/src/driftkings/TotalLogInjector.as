package driftkings
{
	import mods.common.AbstractComponentInjector;
	import driftkings.views.battle.TotalLogUI;
   
	public class TotalLogInjector extends AbstractComponentInjector
	{
		public function TotalLogInjector()
		{
			super();
		}
      
		override protected function onPopulate() : void
		{
			autoDestroy = false;
			componentName = "TotalLogView";
			componentUI = TotalLogUI;
			super.onPopulate();
		}
	}
}