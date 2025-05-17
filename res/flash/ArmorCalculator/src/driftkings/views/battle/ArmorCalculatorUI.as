package driftkings.views.battle
{
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.TextExt;
	import mods.common.BattleDisplayable;

	public class ArmorCalculatorUI extends BattleDisplayable
	{
		private var armorCalc:TextExt;
		public var getSettings:Function;

		public function ArmorCalculatorUI()
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
				this.armorCalc = new TextExt(settings.position.x, settings.position.y, Constants.largeText, TextFieldAutoSize.CENTER, this);
			}
		}

		override protected function onBeforeDispose():void 
		{
			super.onBeforeDispose();
			this.armorCalc = null;
		}

		public function as_onCrosshairPositionChanged(x:Number, y:Number):void
		{
			this.x = x;
			this.y = y;
		}

		public function as_armorCalculator(text:String):void
		{
			if (armorCalc)
			{
				this.armorCalc.htmlText = text;
			}
		}
	}
}