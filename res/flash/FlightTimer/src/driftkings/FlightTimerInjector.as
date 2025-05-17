package driftkings
{
   import driftkings.views.battle.FlightTimerUI;
   import mods.common.AbstractViewInjector;
   import mods.common.IAbstractInjector;
   import flash.display3D.VertexBuffer3D;

   public class FlightTimerInjector extends AbstractViewInjector implements IAbstractInjector
   {
	   public function FlightTimerInjector()
		{
			super();
		}

		override public function get componentUI() : Class
		{
			return FlightTimerUI;
		}

		override public function get componentName() : String
		{
			return "FlightTimerView";
		}
	}
}