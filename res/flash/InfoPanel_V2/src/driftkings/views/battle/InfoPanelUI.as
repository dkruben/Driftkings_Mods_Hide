package driftkings.views.battle
{
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.TextExt;
	import mods.common.BattleDisplayable;
	
	public class InfoPanelUI extends BattleDisplayable
	{
		private var infoPanel:TextExt;
		public var getSettings:Function;

		public function InfoPanelUI()
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
				this.infoPanel = new TextExt(settings.position.x, settings.position.y, null, TextFieldAutoSize.CENTER, this);
			}
		}
		
		public function as_onCrosshairPositionChanged(x:Number, y:Number):void
		{
			this.x = x;
			this.y = y;
		}
		
		public function as_infoPanel(text:String):void
		{
			if (infoPanel)
			{
				this.infoPanel.htmlText = text;
			}
		}
	}
}