package driftkings.views.utils
{
	import flash.text.TextFormat;
	
	public class Constants
	{
		public static const middleText:TextFormat   = new TextFormat("$TitleFont", 18, 0xFFFFFF);
		public static const normalText:TextFormat   = new TextFormat("$FieldFont", 16, 0xFFFFFF);
		
		public static const ALPHA:Number            = 0.6;
		public static const BG_ALPHA:Number         = 0.3;
		public static const HUNDREDTH:Number        = 0.01;
		
		public function Constants()
		{
			super();
		}
	}
}