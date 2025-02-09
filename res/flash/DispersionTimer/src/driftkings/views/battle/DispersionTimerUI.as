package driftkings.views.battle
{
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.TextExt;
	import mods.common.BattleDisplayable;
	
	public class DispersionTimerUI extends BattleDisplayable
	{
		private var dispersionTime:TextExt;
		public var getSettings:Function;

		public function DispersionTimerUI()
		{
			super();
			this.tabEnabled = false;
			this.tabChildren = false;
			this.mouseEnabled = false;
			this.mouseChildren = false;
			this.buttonMode = false;
		}
		
		override protected function onPopulate():void 
		{
			var settings:Object = getSettings();
		if (settings.enabled)
			{
				this.x = settings.x < 0 ? parent.width + settings.x : settings.x
				this.y = settings.y < 0 ? parent.height + settings.y : settings.y
				this.dispersionTime = new TextExt(x, y, Constants.middleText, settings.align, this);
			}
		}
		
		override protected function onBeforeDispose():void 
		{
			super.onBeforeDispose();
			this.dispersionTime = null;
		}
		
		public function as_onCrosshairPositionChanged(x:Number, y:Number):void
		{
			this.x = x;
			this.y = y;
		}
		
		public function as_upateTimerText(text:String):void
		{
			this.dispersionTime.htmlText = text;
		}
	}
}