package driftkings.views.battle
{
    import flash.events.Event;
    import driftkings.views.utils.Constants;
    import driftkings.views.utils.TextExt;
    import driftkings.views.utils.Align;
    import mods.common.BattleDisplayable;
    
    public class TotalLogUI extends BattleDisplayable
    {
        private var top_log_inCenter:Boolean = true;
        private var top_log:TextExt = null;

        private var alignX:String = Align.TOP;
        private var alignY:String = Align.LEFT;
        
        public function TotalLogUI()
        {
            super();
            App.stage.addEventListener(Event.RESIZE, this.onResizeHandle);
        }
        
        override protected function onBeforeDispose():void
        {
            App.stage.removeEventListener(Event.RESIZE, this.onResizeHandle);
            super.onBeforeDispose();
            this.top_log = null;
        }
        
        public function as_createTopLog(settings:Object):void
        {
            if (settings == null) return;

            this.alignX = settings.alignX || Align.TOP;
            this.alignY = settings.alignY || Align.LEFT;

            this.top_log_inCenter = settings.inCenter;
            this.top_log = new TextExt(settings.x, settings.y, Constants.largeText, settings.align, this);

            this.updatePosition();
        }
        
        public function as_updateTopLog(text:String):void
        {
            if (this.top_log != null)
			{
                this.top_log.htmlText = text;
            }
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
        
        private function onResizeHandle(event:Event):void
        {
            this.updatePosition();
            if (this.top_log && this.top_log_inCenter)
            {
                this.x = Math.ceil(App.appWidth >> 1);
            }
        }
    }
}