package driftkings
{
	import mods.common.AbstractComponentInjector;
	import driftkings.views.battle.DamageLogsUI;
   
	public class DamageLogsInjector extends AbstractComponentInjector
	{
		public function DamageLogsInjector()
		{
			super();
		}
      
		override protected function onPopulate() : void
		{
			autoDestroy = false;
			componentName = "DamageLogsView";
			componentUI = DamageLogsUI;
			super.onPopulate();
		}
	}
}