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
            disableInteractivity();
        }

        override protected function onPopulate():void
        {
            super.onPopulate();
            var settings:Object = this.getSettings();
            positionUI(settings);
            createDateTimeField(settings);
        }

        private function disableInteractivity():void
        {
            this.tabEnabled = false;
            this.tabChildren = false;
            this.mouseEnabled = false;
            this.mouseChildren = false;
            this.buttonMode = false;
        }

        private function positionUI(settings:Object):void
        {
            this.x = calculatePosition(settings.position.x, parent.width);
            this.y = calculatePosition(settings.position.y, parent.height);
        }

        private function calculatePosition(value:Number, parentSize:Number):Number
        {
            return value < 0 ? parentSize + value : value;
        }

        private function createDateTimeField(settings:Object):void
        {
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