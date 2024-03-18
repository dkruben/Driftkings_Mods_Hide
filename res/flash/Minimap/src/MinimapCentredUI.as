package 
{
   import driftkings.views.battle.MinimapCentred;
   import driftkings.injector.AbstractViewInjector;
   import driftkings.injector.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class MinimapCentredUI extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function MinimapCentredUI()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return MinimapCentred;
		}
      
		override public function get componentName() : String
		{
			return "MinimapCentredView";
		}
	}
}