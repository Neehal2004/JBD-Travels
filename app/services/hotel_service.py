from ..models import Hotel, Destination

class HotelService:
    """
    Hotel Information & Multi-Source Price Comparison Service for JBD Travels.
    Compares standard rates against major OTAs (Booking.com, Expedia) and
    showcases JBD Partner Club exclusive negotiated savings.
    """

    @classmethod
    def search_hotels(cls, destination_query=None, min_stars=None, max_price=None,
                      amenities_filter=None, partner_only=False, sort_by='recommended'):
        query = Hotel.query.filter_by(is_active=True)

        if destination_query:
            query = query.filter(
                (Hotel.city.ilike(f"%{destination_query}%")) |
                (Hotel.country.ilike(f"%{destination_query}%")) |
                (Hotel.name.ilike(f"%{destination_query}%"))
            )

        if min_stars:
            try:
                query = query.filter(Hotel.stars >= int(min_stars))
            except Exception:
                pass

        if partner_only:
            query = query.filter(Hotel.is_partner == True)

        hotels = query.all()

        results = []
        for h in hotels:
            # Check price filter
            if max_price:
                try:
                    if h.jbd_partner_rate > float(max_price):
                        continue
                except Exception:
                    pass

            # Check amenities filter
            if amenities_filter:
                hotel_amenities_lower = [a.lower() for a in h.get_amenities_list()]
                if isinstance(amenities_filter, str):
                    amenities_list = [a.strip().lower() for a in amenities_filter.split(',')]
                else:
                    amenities_list = [str(a).strip().lower() for a in amenities_filter]
                
                # Check if all requested amenities are present
                if not all(any(req in ha for ha in hotel_amenities_lower) for req in amenities_list):
                    continue

            h_dict = h.to_dict()

            # Cross-OTA Price Comparison Data (Simulated comparative marketplace)
            standard = h.standard_rate_per_night
            partner = h.jbd_partner_rate
            expedia_rate = round(standard * 0.98, 2)       # Typical small OTA discount
            booking_rate = round(standard * 0.96, 2)       # Typical OTA genius discount
            jbd_savings = round(min(expedia_rate, booking_rate) - partner, 2)

            h_dict['price_comparison'] = {
                'standard_direct_rate': standard,
                'expedia_rate': expedia_rate,
                'booking_com_rate': booking_rate,
                'jbd_exclusive_partner_rate': partner,
                'discount_percent': h.partner_discount_percent,
                'customer_savings_vs_competitor': max(0.0, jbd_savings),
                'best_price_guarantee': True
            }

            results.append(h_dict)

        # Sorting
        if sort_by == 'price_low':
            results.sort(key=lambda x: x['jbd_partner_rate'])
        elif sort_by == 'price_high':
            results.sort(key=lambda x: x['jbd_partner_rate'], reverse=True)
        elif sort_by == 'stars':
            results.sort(key=lambda x: x['stars'], reverse=True)
        elif sort_by == 'discount':
            results.sort(key=lambda x: x['partner_discount_percent'], reverse=True)
        else: # recommended
            results.sort(key=lambda x: (x['is_partner'], x['rating'], x['stars']), reverse=True)

        return results

    @classmethod
    def get_hotel_details(cls, hotel_id):
        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            return None
        
        data = hotel.to_dict()
        standard = hotel.standard_rate_per_night
        partner = hotel.jbd_partner_rate
        
        data['price_comparison'] = {
            'standard_direct_rate': standard,
            'expedia_rate': round(standard * 0.98, 2),
            'booking_com_rate': round(standard * 0.96, 2),
            'jbd_exclusive_partner_rate': partner,
            'discount_percent': hotel.partner_discount_percent,
            'customer_savings_vs_competitor': round(max(0.0, (standard * 0.96) - partner), 2),
            'best_price_guarantee': True
        }
        return data
