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
			this.config = settings;
			var x:int = settings.x;
			if (x < 0)
			{
				x = App.appWidth + x;
			}
			var y:int = settings.y;
			if (y < 0)
			{
				y = App.appHeight + y;
			}
			this.dispersionTime = new TextExt(x, y, Constants.middleText, settings.align, this);
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
			var x:int = config.x;
			if (x < 0)
			{
				x = App.appWidth + x;
			}
			var y:int = config.y;
			if (y < 0)
			{
				y = App.appHeight + y;
			}
			dispersionTime.x = x;
			dispersionTime.y = y;
		}
	}
}