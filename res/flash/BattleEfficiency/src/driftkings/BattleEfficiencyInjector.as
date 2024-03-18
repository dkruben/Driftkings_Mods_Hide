package driftkings
{
   import driftkings.views.battle.BattleEfficiencyUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class BattleEfficiencyInjector extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function BattleEfficiencyInjector()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return BattleEfficiencyUI;
		}
      
		override public function get componentName() : String
		{
			return "BattleEfficiencyView";
		}
	}
}