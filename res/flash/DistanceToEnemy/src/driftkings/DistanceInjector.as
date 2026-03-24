package driftkings
{
   import driftkings.views.battle.DistanceUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class DistanceInjector extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function DistanceInjector()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return DistanceUI;
		}
      
		override public function get componentName() : String
		{
			return "DistanceView";
		}
	}
}