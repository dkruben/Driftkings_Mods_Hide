package driftkings
{
	import mods.common.AbstractComponentInjector;
	import driftkings.views.InfoPanelUI;
   
	public class InfoPanelInjector extends AbstractComponentInjector
	{
		public function InfoPanelInjector()
		{
			super();
		}
      
		override protected function onPopulate() : void
		{
			autoDestroy = false;
			componentName = "InfoPanelView";
			componentUI = InfoPanelUI;
			super.onPopulate();
		}
	}
}