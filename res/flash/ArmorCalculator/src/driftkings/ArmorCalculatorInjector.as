package driftkings
{
   import driftkings.views.battle.ArmorCalculatorUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class ArmorCalculatorInjector extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function ArmorCalculatorInjector()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return ArmorCalculatorUI;
		}
      
		override public function get componentName() : String
		{
			return "ArmorCalculatorView";
		}
	}
}