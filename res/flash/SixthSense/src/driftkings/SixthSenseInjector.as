package driftkings
{
   import driftkings.views.battle.SixthSenseUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class SixthSenseInjector extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function SixthSenseInjector()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return SixthSenseUI;
		}
      
		override public function get componentName() : String
		{
			return "SixthSenseView";
		}
	}
}