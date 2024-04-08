package driftkings
{
   import driftkings.views.battle.InfoPanelUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class InfoPanelInjector extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function InfoPanelInjector()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return InfoPanelUI;
		}
      
		override public function get componentName() : String
		{
			return "InfoPanelView";
		}
	}
}