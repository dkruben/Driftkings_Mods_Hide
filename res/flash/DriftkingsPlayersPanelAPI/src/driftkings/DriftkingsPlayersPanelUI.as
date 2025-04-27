package driftkings
{
   import driftkings.views.battle.DriftkingsPlayersPanelAPI;
   import mods.common.AbstractViewInjector;
   
   public class DriftkingsPlayersPanelUI extends AbstractViewInjector
   {
	
	   public function DriftkingsPlayersPanelUI()
		{
			super();
		}
		
		override protected function onPopulate() : void
		{
			autoDestroy = false;
			componentName = "DriftkingsPlayersPanelAPI";
			componentUI = DriftkingsPlayersPanelAPI;
			super.onPopulate();
		}
	}
}