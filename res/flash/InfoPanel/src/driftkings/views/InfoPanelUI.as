package driftkings.views
{
	import flash.events.Event;
	import mods.common.BattleDisplayable;
   
	public class InfoPanelUI extends BattleDisplayable
	{
		private static const _defaultX:Number = 596;
		private static const _defaultY:Number = 547;
		
		public var onUpdatePosition:Function = null;
		private var textFlash:InfoPanel = null;
      
		public function InfoPanelUI()
		{
			super();
			this.textFlash = new InfoPanel();
			this.textFlash.addEventListener(Event.CHANGE,this.handleEventChange);
			addChild(this.textFlash);
		}
      
		override protected function onDispose() : void
		{
			removeChild(this.textFlash);
			this.textFlash.removeEventListener(Event.CHANGE,this.handleEventChange);
			this.textFlash.dispose();
			this.textFlash = null;
			super.onDispose();
		}
      
		private function handleEventChange(e:Event) : void
		{
			this.onUpdatePosition(this.textFlash.posX, this.textFlash.posY);
		}
      
		public function as_setScale(textWidth:Number, textHeight:Number) : void
		{
			this.textFlash.setScale(textWidth, textHeight);
		}
      
		public function as_setText(labelText:String) : void
		{
			this.textFlash.setText(labelText);
		}
		
		public function as_hide(delay:int = 0): void
		{
			this.textFlash.hide(delay)
		}
      
		public function as_setVisible(visible:Boolean) : void
		{
			this.textFlash.setVisible(visible);
		}
      
		public function as_setVisibleBB(isVisible:Boolean) : void
		{
			this.textFlash.setVisibleBB(isVisible);
		}
      
		public function as_setPosition(posX:Number, posY:Number, isSave:Boolean = true) : void
		{
			this.textFlash.setPosition(posX, posY, isSave);
		}
		
		public function as_setDefaultPosition() : void
		{
			this.textFlash.setPosition(_defaultX, _defaultY, true);
		}
      
		public function as_setShadow(linkage:Object) : void
		{
			this.textFlash.setShadow(linkage);
		}
		
		public function as_isDraggable(isDrag:Boolean): void
		{
			this.textFlash.isDraggable(isDrag);
		}
	}
}