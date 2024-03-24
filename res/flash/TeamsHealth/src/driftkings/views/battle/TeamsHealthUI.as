package driftkings.views.battle
{
	import flash.events.Event;
	import mods.common.BattleDisplayable;
	import driftkings.views.battle.interfaces.ITeamHealth;
	import net.wg.data.constants.generated.BATTLE_VIEW_ALIASES;
	
	public class TeamsHealthUI extends BattleDisplayable
		
	{
		public var getSettings:Function;
		public var isColorBlind:Function;
		public var getColors:Function;
		
		private var hpBars:ITeamHealth;
		private var correlation:*   = null;
		
		public function TeamsHealthUI()
		{
			super();
		}
		
		override protected function onPopulate():void
		{
			super.onPopulate();
			var settings:Object = this.getSettings();
			this.x = App.appWidth >> 1;
			
			if (settings.style == "league")
			{
				this.hpBars = this.addChild(new League(this.isColorBlind(), this.getColors().colors)) as ITeamHealth;
			}
			else
			{
				this.hpBars = this.addChild(new Default(this.isColorBlind(), this.getColors().colors)) as ITeamHealth;
			}
			var page:* = parent;
			this.correlation = page.getComponent(BATTLE_VIEW_ALIASES.FRAG_CORRELATION_BAR);
			var background:* = this.correlation.getChildAt(0);
			background.y = -22;
			background.alpha = 0.9;
			this.correlation.y = 20;
			this.updateCorrelationBar();
		}
		
		private function updateCorrelationBar():void
		{
			this.correlation.removeChild(this.correlation.greenBackground);
			this.correlation.removeChild(this.correlation.redBackground);
			this.correlation.removeChild(this.correlation.purpleBackground);
			this.correlation.removeChild(this.correlation.teamFragsSeparatorField);
			this.correlation.removeChild(this.correlation.allyTeamFragsField);
			this.correlation.removeChild(this.correlation.enemyTeamFragsField);
			this.correlation.removeChild(this.correlation.allyTeamHealthBar);
			this.correlation.removeChild(this.correlation.enemyTeamHealthBar);
		}
		
		public function as_updateCountersPosition(ally:Number, enemy:Number):void
		{
			this.correlation.allyVehicleMarkersList._markerStartPosition = ally//-25;
			this.correlation.enemyVehicleMarkersList._markerStartPosition = enemy//-5;
			this.correlation.allyVehicleMarkersList.sort();
			this.correlation.enemyVehicleMarkersList.sort();
		}
		
		override protected function onBeforeDispose():void
		{
			super.onBeforeDispose();
			this.hpBars.remove();
			this.hpBars = null;
			this.correlation = null;
		}
		
		public function as_colorBlind(enabled:Boolean):void
		{
			this.hpBars.setColorBlind(enabled);
		}
		
		public function as_updateHealth(alliesHP:int, enemiesHP:int, totalAlliesHP:int, totalEnemiesHP:int):void
		{
			this.hpBars.update(alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP);
		}
		
		public function as_updateScore(ally:int, enemy:int):void
		{
			this.hpBars.updateScore(ally, enemy);
		}
		
		private function onResizeHandle(event:Event):void
		{
			this.x = App.appWidth >> 1;
		}
	}
}