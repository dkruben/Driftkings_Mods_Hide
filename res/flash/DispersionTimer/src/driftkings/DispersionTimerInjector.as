package driftkings
{
   import driftkings.views.battle.DispersionTimerUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class DispersionTimerInjector extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function DispersionTimerInjector()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return DispersionTimerUI;
		}
      
		override public function get componentName() : String
		{
			return "DispersionTimerView";
		}
	}
}