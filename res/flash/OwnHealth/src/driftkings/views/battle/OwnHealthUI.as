package driftkings.views.battle
{
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.ProgressBar;
	import mods.common.BattleDisplayable;
	
	public class OwnHealthUI extends BattleDisplayable
	{
		private var own_health:ProgressBar;
		public var getAVGColor:Function;
		public var getSettings:Function;
		
		public function OwnHealthUI()
		{
			super();
		}
		
		override protected function configUI():void
		{
			super.configUI();
			this.tabEnabled = false;
			this.tabChildren = false;
			this.mouseEnabled = false;
			this.mouseChildren = false;
			this.buttonMode = false;
		}
		
		override protected function onPopulate():void 
		{
			super.onPopulate();
			this.onResizeHandle(null);
			var settings:Object = this.getSettings();
			var colors:Object = this.getSettings().colors;
			this.own_health = new ProgressBar(settings.x - 90, settings.y, 180, 22, this.getAVGColor(), colors.bgColor, 0.2);
			this.own_health.setOutline(180, 22);
			this.own_health.addTextField(90, -3, TextFieldAutoSize.CENTER, Constants.middleText);
			this.addChild(this.own_health);
		}
		
		override protected function onBeforeDispose():void 
		{
			super.onBeforeDispose();
			this.own_health.remove()
			this.own_health = null;
		}
		
		public function as_setOwnHealth(scale:Number, text:String, color:String):void
		{
			this.own_health.setNewScale(scale);
			this.own_health.setText(text);
			this.own_health.updateColor(color);
		}
		
		public function as_BarVisible(vis:Boolean):void
		{
			this.own_health.visible = vis;
		}
		
		private function onResizeHandle(event:Event):void 
		{
			this.x = App.appWidth >> 1;
			this.y = App.appHeight >> 1;
		}
		
		public function as_onCrosshairPositionChanged(x:Number, y:Number):void
		{
			this.x = x;
			this.y = y;
		}
	}
}