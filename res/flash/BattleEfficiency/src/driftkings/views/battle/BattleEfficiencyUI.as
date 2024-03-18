package driftkings.views.battle
{
	import flash.events.Event;
	import flash.text.TextFieldAutoSize;
	//
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.TextExt;
	//
	import mods.common.BattleDisplayable;
	
	public class BattleEfficiencyUI extends BattleDisplayable
	{
		private var battleEff:TextExt;
		private var config:Object;
		public var getShadowSettings:Function;

		public function BattleEfficiencyUI()
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
			this.battleEff = null;
			App.utils.data.cleanupDynamicObject(this.config);
		}
		
		public function as_startUpdate(settings:Object): void
		{
			this.as_clearScene();
			if (settings.enabled)
			{
				this.config = settings
				this.x = settings.position.x < 0 ? parent.width + settings.position.x : settings.position.x
				this.y = settings.position.y < 0 ? parent.height + settings.position.y : settings.position.y
				this.battleEff = new TextExt(settings.position.x, settings.position.y, Constants.tite16, TextFieldAutoSize.CENTER, getShadowSettings(), this);
			}
		}
		
		public function as_battleEff(text:String):void
		{
			if (battleEff)
			{
				this.battleEff.htmlText = text;
			}
		}
		
		private function _onResizeHandle(e:Event):void
		{
			this.x = this.config.position.x < 0 ? parent.width + this.config.position.x : this.config.position.x
			this.y = this.config.position.y < 0 ? parent.height + this.config.position.y : this.config.position.y
		}
	}
}