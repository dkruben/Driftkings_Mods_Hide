package driftkings.views.battle
{
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.TextExt;
	import mods.common.BattleDisplayable;
	
	public class BattleClockUI extends BattleDisplayable
	{
		private var dateTime:TextExt;
		public var getSettings:Function;

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
		}
		
		override protected function onPopulate():void 
		{
			super.onPopulate();
			var settings:Object = this.getSettings();
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
	}
}