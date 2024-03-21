package driftkings
{
   import driftkings.views.battle.MainGunUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;
   
   public class MainGunInjector extends AbstractViewInjector implements IAbstractInjector
   {
	
	   public function MainGunInjector()
		{
			super();
		}
      
		override public function get componentUI() : Class
		{
			return MainGunUI;
		}
      
		override public function get componentName() : String
		{
			return "MainGunView";
		}
	}
}