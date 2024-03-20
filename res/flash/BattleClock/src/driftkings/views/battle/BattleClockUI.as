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
			this.as_clearScene();
			super.onDispose();
		}
		
			public function as_clearScene():void
		{
			while (this.numChildren > 0)
			{
				this.removeChildAt(0);
			}
			this.dateTime = null;
		}
		
		public function as_startUpdate(settings:Object):void
		{
			this.config = settings;
			this.x = settings.position.x < 0 ? parent.width + settings.position.x : settings.position.x
			this.y = settings.position.y < 0 ? parent.height + settings.position.y : settings.position.y
			dateTime = new TextExt(settings.position.x, settings.position.y, Constants.normalText, TextFieldAutoSize.LEFT, this);
		}
		
		public function as_setDateTime(text:String):void
		{
			if (dateTime)
			{
				dateTime.htmlText = text;
			}
		}
		

		public function _onResizeHandle(event:Event):void
		{
			this.x = this.config.position.x < 0 ? parent.width + this.config.position.x : this.config.position.x
			this.y = this.config.position.y < 0 ? parent.height + this.config.position.y : this.config.position.y
		}
	}
}