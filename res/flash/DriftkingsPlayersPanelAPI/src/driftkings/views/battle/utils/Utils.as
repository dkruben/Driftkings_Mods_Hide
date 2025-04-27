package driftkings.views.battle.utils
{
	import flash.filters.BitmapFilterQuality;
	import flash.filters.DropShadowFilter;

	public class Utils
	{
		private static const ALPHA_FACTOR:Number = 0.01;
		private static const STRENGTH_FACTOR:Number = 0.01;
		private static const MAX_BLUR:Number = 255;
		private static const MAX_STRENGTH:Number = 255;
		private static const MIN_ANGLE:Number = 0;
		private static const MAX_ANGLE:Number = 360;

		public function Utils()
		{
			super();
		}

		public static function colorConvert(color:String) : uint
		{
			return uint(parseInt(color.split("#").join("0x"), 16));
		}

		public static function getDropShadowFilter(distance:Number, angle:Number, color:String, alpha:Number, blurX:Number, blurY:Number, strength:Number): DropShadowFilter
		{
			var filter:DropShadowFilter = new DropShadowFilter();
			filter.distance = distance;
			filter.angle = clamp(angle, MIN_ANGLE, MAX_ANGLE);
			filter.color = colorConvert(color);
			filter.alpha = clamp(ALPHA_FACTOR * alpha, 0, 1);
			filter.blurX = clamp(blurX, 0, MAX_BLUR);
			filter.blurY = clamp(blurY, 0, MAX_BLUR);
			filter.strength = clamp(STRENGTH_FACTOR * strength, 0, MAX_STRENGTH);
			filter.quality = BitmapFilterQuality.MEDIUM;
			filter.inner = false;
			filter.knockout = false;
			filter.hideObject = false;
			return filter;
		}

		public static function clamp(value:Number, min:Number, max:Number) : Number
		{
			return Math.max(min, Math.min(max, value));
		}
	}
}