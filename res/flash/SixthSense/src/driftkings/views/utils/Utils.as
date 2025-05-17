package driftkings.views.utils
{
    import flash.display.DisplayObject;
    import flash.geom.ColorTransform;

    public class Utils
    {
        public static function colorConvert(color:String):uint
        {
            var cleanColor:String = color.charAt(0) == '#' ? color.substr(1) : color;
            return uint(parseInt(cleanColor, 16));
        }

        public static function updateColor(object:DisplayObject, hpColor:String):void
        {
            var colorInfo:ColorTransform = object.transform.colorTransform;
            colorInfo.color = colorConvert(hpColor);
            object.transform.colorTransform = colorInfo;
        }
    }
}