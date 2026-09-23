# Supabase and Kotlin serialization use generated serializers. Keep model metadata in release builds.
-keepattributes *Annotation*, InnerClasses
-keepclassmembers class **$$serializer { <fields>; }
