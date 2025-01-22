package driftkings.views.utils
{
	public class Utils
	{
		public static function colorConvert(color:String):uint
		{
			return uint(parseInt(color.substr(1), 16));
		}
	}
}