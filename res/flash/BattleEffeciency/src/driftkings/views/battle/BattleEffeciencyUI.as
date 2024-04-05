package driftkings.views.battle
{
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.TextExt;
	import mods.common.BattleDisplayable;
	
	public class BattleEffeciencyUI extends BattleDisplayable
	{
		private var battleEff:TextExt;
		public var getSettings:Function;

		public function BattleEffeciencyUI()
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
			if (settings.enabled)
			{
				this.x = settings.position.x < 0 ? parent.width + settings.position.x : settings.position.x
				this.y = settings.position.y < 0 ? parent.height + settings.position.y : settings.position.y
				this.battleEff = new TextExt(settings.position.x, settings.position.y, null, settings.textShadow, TextFieldAutoSize.CENTER, this);
			}
		}
		
		public function as_battleEff(text:String):void
		{
			if (battleEff)
			{
				this.battleEff.htmlText = text;
			}
		}
	}
}