package driftkings
{
   import driftkings.views.battle.BattleEffeciencyUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class BattleEffeciencyInjector extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function BattleEffeciencyInjector()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return BattleEffeciencyUI;
		}
      
		override public function get componentName() : String
		{
			return "BattleEffeciencyView";
		}
	}
}