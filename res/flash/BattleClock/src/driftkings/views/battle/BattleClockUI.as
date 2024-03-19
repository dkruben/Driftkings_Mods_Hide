package driftkings.views.battle
{
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	//
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.TextExt;
	//
	import mods.common.BattleDisplayable;
	
	public class BattleClockUI extends BattleDisplayable
	{
		private var dateTime:TextExt;
		private var config:Object;
		public var getShadowSettings:Function;

		public function BattleClockUI()
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
			this.addEventListener(Event.RESIZE, this._onResizeHandle);
		}
		
		override protected function onDispose():void
		{
			this.removeEventListener(Event.RESIZE, this._onResizeHandle);
			super.onDispose();
		}
		
		public function as_startUpdate(settings:Object):void
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
			dateTime = new TextExt(x, y, TextFieldAutoSize.LEFT, getShadowSettings(), this);
		}
		
		public function as_setDateTime(text:String):void
		{
			if (dateTime)
			{
				dateTime.htmlText = text;
			}
		}
		
		public function as_onCrosshairPositionChanged(x:Number, y:Number):void
		{
			this.x = x;
			this.y = y;
		}
		

		public function _onResizeHandle(event:Event):void
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
			dateTime.x = x;
			dateTime.y = y;
		}
	}
}