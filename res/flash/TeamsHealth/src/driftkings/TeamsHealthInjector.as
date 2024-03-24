package driftkings
{
   import driftkings.views.battle.TeamsHealthUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class TeamsHealthInjector extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function TeamsHealthInjector()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return TeamsHealthUI;
		}
      
		override public function get componentName() : String
		{
			return "TeamsHealthView";
		}
	}
}