package driftkings.views.battle
{
	import flash.events.Event;
    import driftkings.views.utils.Constants;
    import driftkings.views.utils.Align;
    import driftkings.views.utils.TextExt;
    import mods.common.BattleDisplayable;
    
    public class FlightTimerUI extends BattleDisplayable
    {
        private var flightTime:TextExt;
        private var alignX:String = Align.CENTER;
        private var alignY:String = Align.CENTER;
        
        public var getSettings:Function;
        
        public function FlightTimerUI()
        {
            super();
            this.tabEnabled = false;
            this.tabChildren = false;
            this.mouseEnabled = false;
            this.mouseChildren = false;
            this.buttonMode = false;
            this.addEventListener(Event.RESIZE, onResizeHandle);
        }
        
        override protected function onPopulate():void 
        {
            super.onPopulate();
            if (this.getSettings != null) {
                var settings:Object = this.getSettings();
                if (settings != null)
				{
                    this.alignX = settings.alignX || Align.CENTER;
                    this.alignY = settings.alignY || Align.CENTER;
                    this.flightTime = new TextExt(settings.x, settings.y, Constants.middleText, settings.align, this);
                    this.updatePosition();
                }
            }
        }
        
        override protected function onBeforeDispose():void 
        {
            super.onBeforeDispose();
            this.flightTime = null;
            this.removeEventListener(Event.RESIZE, onResizeHandle);
        }
        
        private function updatePosition() : void
        {
            var posX:Number = App.appWidth >> 1;
            var posY:Number = App.appHeight >> 1;
            switch(this.alignX)
            {
                case Align.LEFT:
                    posX = 0;
                    break;
                case Align.RIGHT:
                    posX = App.appWidth;
                    break;
            }
            switch(this.alignY)
            {
                case Align.TOP:
                    posY = 0;
                    break;
                case Align.BOTTOM:
                    posY = App.appHeight;
                    break;
            }
            this.x = posX;
            this.y = posY;
        }
        
        public function as_onCrosshairPositionChanged(x:Number, y:Number):void
        {
            this.x = x;
            this.y = y;
        }
        
        private function onResizeHandle(event:Event) : void
        {
            this.updatePosition();
        }
        
        public function as_flightTime(text:String):void
        {
            this.flightTime.htmlText = text;
        }
    }
}