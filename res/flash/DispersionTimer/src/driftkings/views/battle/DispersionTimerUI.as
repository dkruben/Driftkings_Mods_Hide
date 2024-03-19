package driftkings.views.battle
{
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	//
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.TextExt;
	//
	import mods.common.BattleDisplayable;
	
	public class DispersionTimerUI extends BattleDisplayable
	{
		private var dispersionTime:TextExt;
		private var config:Object;

		public function DispersionTimerUI()
		{
			super();
			//this.tabEnabled = false;
			//this.tabChildren = false;
			//this.mouseEnabled = false;
			//this.mouseChildren = false;
			//this.buttonMode = false;
			this.addEventListener(Event.RESIZE, this._onResizeHandle);
		}
		
		override protected function onDispose():void
		{
			this.removeEventListener(Event.RESIZE, this._onResizeHandle);
			this.as_clearScene();
			super.onDispose();
		}
		
		public function as_clearScene():void
		{
			while (this.numChildren > 0){
				this.removeChildAt(0);
			}
			this.dispersionTime = null;
			//App.utils.data.cleanupDynamicObject(this.config);
		}
		
		public function as_startUpdate(settings:Object): void
		{
		if (settings.enabled)
			{
				this.config = settings;
				this.x = settings.x < 0 ? parent.width + settings.x : settings.x
				this.y = settings.y < 0 ? parent.height + settings.y : settings.y
				this.dispersionTime = new TextExt(x, y, Constants.middleText, settings.align, this);
			}
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
		
		private function _onResizeHandle(event:Event):void
		{
			this.x = config.x < 0 ? parent.width + config.x : config.x
			this.y = config.y < 0 ? parent.height + config.y : config.y
		}
	}
}