package driftkings
{
   import driftkings.views.battle.BattleClockUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class BattleClockInjector extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function BattleClockInjector()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return BattleClockUI;
		}
      
		override public function get componentName() : String
		{
			return "BattleClockView";
		}
	}
}