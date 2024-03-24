package driftkings.views.battle
{
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.TextExt;
	import mods.common.BattleDisplayable;
	
	public class DistanceUI extends BattleDisplayable
	{
		public var getSettings:Function;
		private var distance:TextExt;
		
		public function DistanceUI()
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
			this.distance = new TextExt(settings.x, settings.y, Constants.middleText, settings.align, this);
		}
		
		override protected function onBeforeDispose():void 
		{
			super.onBeforeDispose();
			this.distance = null;
		}
		
		public function as_onCrosshairPositionChanged(x:Number, y:Number):void
		{
			this.x = x;
			this.y = y;
		}
		
		public function as_setDistance(text:String):void
		{
			this.distance.htmlText = text;
		}
	}
}